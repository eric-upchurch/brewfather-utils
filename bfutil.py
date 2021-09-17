import argparse
import copy
import json
import os
from datetime import date, datetime, time

SIX_HOURS_MILLIS = 6 * 60 * 60 * 1000
USE_METRIC = False


def load_object(filename):
    with open("templates/" + filename) as f:
        obj = json.load(f)
        return obj


def to_epoch_millis(date_str):
    the_date = date.fromisoformat(date_str)
    brew_date = datetime.combine(the_date, time(12))  # noon local
    return int(brew_date.timestamp() * 1000)


def gal_to_l(volume):
    return volume if USE_METRIC else volume * 3.78541


def get_by_entry(array, key, value, key_to_get):
    for obj in array:
        if key in obj and obj[key] == value and key_to_get in obj:
            return obj[key_to_get]
    return None


def f_to_c(temp):
    return temp if USE_METRIC else (temp - 32) / 1.8


def get_actual_og(i_brew):
    if "batchActOG" in i_brew and i_brew["batchActOG"] != 1:
        return i_brew["batchActOG"]
    return i_brew["batchEstOG"]


def get_actual_fg(i_brew):
    if "batchActFG" in i_brew and i_brew["batchActFG"] != 1:
        return i_brew["batchActFG"]
    return i_brew["batchEstFG"]


def get_actual_abv(i_brew):
    if "batchActABV" in i_brew:
        return i_brew["batchActABV"]

    return (get_actual_og(i_brew) - get_actual_fg(i_brew)) * 131.25


def get_mash_step(i_brew):
    if "batchSteps" in i_brew:
        batch_steps = i_brew["batchSteps"]
        for step in batch_steps:
            if step["bsName"] == "Infusion":
                return step["bsStepTemp"], step["bsTime"]
    return None, None


def get_value(i_brew, key, default):
    if key in i_brew:
        return i_brew[key]
    else:
        print(f"  - Missing key [{key}], returning {default}")
        return default


def oz_to_g(weight):
    return weight if USE_METRIC else weight * 28.3495


def oz_to_kg(weight):
    return weight / 1000 if USE_METRIC else oz_to_g(weight) / 1000


def base_malt_type(i_type):
    if i_type in BFUtil.BASE_MALT_TYPES:
        return BFUtil.BASE_MALT_TYPES[i_type]
    return None


def grain_type(i_type):
    if i_type in BFUtil.GRAIN_TYPES:
        return BFUtil.GRAIN_TYPES[i_type]
    return i_type


def oz_to_ml(volume):
    return volume if USE_METRIC else volume * 29.5735


class BFUtil:
    OBJ_YEAST = load_object("yeast.json")
    OBJ_FERM = load_object("fermentable.json")
    OBJ_HOPS = load_object("hops.json")
    OBJ_MASH_STEP = load_object("mash-step.json")
    EXTRAS_MAP = load_object("extras_map.json")
    BF_DEFAULT_MASH = load_object("default-mash.json")
    BF_EQUIPMENT = load_object("equipment.json")  # TODO Make this a command-line arg for other users
    BF_TEMPLATE = load_object("brewfather-batch.json")

    BASE_MALT_TYPES = dict()
    BASE_MALT_TYPES["Base - 2 Row"] = "Base"
    BASE_MALT_TYPES["Base - Munich"] = "Base (Munich)"
    BASE_MALT_TYPES["Base - Other"] = "Base"
    BASE_MALT_TYPES["Base - Wheat"] = "Base (Wheat)"
    BASE_MALT_TYPES["Crystal Malt"] = "Crystal/Caramel"
    BASE_MALT_TYPES["Roasted / Toasted Malt"] = "Roasted"
    BASE_MALT_TYPES["N/A"] = None

    GRAIN_TYPES = dict()
    GRAIN_TYPES["Dry Malt Extract"] = "Dry Extract"
    GRAIN_TYPES["Liquid Malt Extract"] = "Liquid Extract"

    def __init__(self):
        self.batch_number = 1
        self.brewer = "Brewer"

    def convert(self, i_brew):
        # Copy the Brewfather template
        bf = copy.deepcopy(BFUtil.BF_TEMPLATE)

        bf["batchNo"] = self.batch_number
        print(f"Processing {i_brew['batchName']} as Batch #{self.batch_number}")

        # Set equipment and brewer
        bf["recipe"]["equipment"] = copy.deepcopy(BFUtil.BF_EQUIPMENT)
        bf["brewer"] = self.brewer
        bf["recipe"]["author"] = self.brewer

        # Set date/times
        brew_datetime = to_epoch_millis(i_brew["batchBrewDate"])
        bottling_datetime = to_epoch_millis(i_brew["batchEstServeDate"])
        ferm_datetime = brew_datetime + SIX_HOURS_MILLIS
        bf["brewDate"] = brew_datetime
        bf["bottlingDate"] = bottling_datetime
        bf["fermentationStartDate"] = ferm_datetime

        # "notes" contains three entries in reverse chronological order for
        # Completed, Fermenting, Brewing
        notes = bf["notes"]
        notes[0]["timestamp"] = bottling_datetime
        notes[1]["timestamp"] = ferm_datetime
        notes[2]["timestamp"] = brew_datetime

        if "batchNotes" in i_brew and i_brew["batchNotes"] != "":
            notes[0]["note"] = i_brew["batchNotes"]

        # Set stats
        ibu = get_value(i_brew, "batchEstIBU", 0)
        og = get_actual_og(i_brew)
        bf["estimatedColor"] = i_brew["batchColor"]
        bf["estimatedFg"] = i_brew["batchEstFG"]
        bf["estimatedIbu"] = ibu
        bf["estimatedOg"] = i_brew["batchEstOG"]
        bf["measuredAbv"] = get_actual_abv(i_brew)
        bf["measuredFg"] = get_actual_fg(i_brew)
        bf["measuredOg"] = get_actual_og(i_brew)
        bf["measuredEfficiency"] = i_brew["batchEfficiency"]

        # Recipe
        recipe = bf["recipe"]
        recipe["abv"] = i_brew["batchEstABV"]
        recipe["batchSize"] = gal_to_l(i_brew["batchSize"])
        recipe["boilSize"] = gal_to_l(i_brew["batchBoilSize"])
        recipe["boilTime"] = get_value(i_brew, "batchBoilTime", 0)
        recipe["color"] = i_brew["batchColor"]
        recipe["efficiency"] = i_brew["batchEfficiency"]
        recipe["fgEstimated"] = i_brew["batchEstFG"]
        recipe["ibu"] = ibu
        recipe["name"] = i_brew["batchName"]
        recipe["og"] = i_brew["batchEstOG"]
        recipe["totalGravity"] = i_brew["batchEstOG"]
        recipe["postBoilGravity"] = i_brew["batchEstOG"]
        recipe["preBoilGravity"] = get_value(i_brew, "batchPreBoilOG", og)
        recipe["type"] = get_value(i_brew, "batchType", "All Grain")

        # Fermentation profile
        if "batchFerms" in i_brew:
            temp = get_by_entry(i_brew["batchFerms"], "bfName", "Primary", "bfTemp")
            if temp is not None:
                recipe["primaryTemp"] = f_to_c(temp)

        # Mash profile and name
        self.populate_mash(bf, i_brew)

        # Hops
        if "batchHops" in i_brew:
            for hop in i_brew["batchHops"]:
                self.add_hops(bf, hop)

        # Fermentables (grain, sugar, adjuncts)
        for fermentable in i_brew["batchGrains"]:
            self.add_fermentable(bf, fermentable)

        # Yeasts
        for yeast in i_brew["batchYeasts"]:
            self.add_yeast(bf, yeast)

        # Additions (finings, nutrients, spices, flavorings, etc.)
        if "batchExtras" in i_brew:
            for extra in i_brew["batchExtras"]:
                self.add_extra(bf, extra)

        self.batch_number += 1
        return bf

    @staticmethod
    def add_hops(bf, hop):
        bf_hop = copy.deepcopy(BFUtil.OBJ_HOPS)

        bf_hop["alpha"] = hop["bhAlpha"]
        bf_hop["amount"] = oz_to_g(hop["bhAmount"])
        bf_hop["name"] = hop["bhName"]
        bf_hop["origin"] = hop["bhHopOrigin"]
        bf_hop["time"] = get_value(hop, "bhBoilTime", 0)
        bf_hop["type"] = hop["bhHopForm"]
        bf_hop["use"] = hop["bhHopUse"]

        bf["batchHops"].append(bf_hop)
        bf["recipe"]["hops"].append(bf_hop)

    @staticmethod
    def add_fermentable(bf, fermentable):
        bf_ferm = copy.deepcopy(BFUtil.OBJ_FERM)

        the_type = grain_type(get_value(fermentable, "bgGrainType", "Sugar"))  # don't know, assume Sugar
        bf_ferm["amount"] = oz_to_kg(get_value(fermentable, "bgAmount", 0))
        bf_ferm["color"] = get_value(fermentable, "bgColor", 0)
        bf_ferm["name"] = fermentable["bgName"]
        bf_ferm["origin"] = fermentable["bgGrainOrigin"]
        bf_ferm["potential"] = fermentable["bgSG"]
        bf_ferm["type"] = the_type
        if "bgBaseMaltType" in fermentable:
            bf_ferm["grainCategory"] = base_malt_type(fermentable["bgBaseMaltType"])

        bf["batchFermentables"].append(bf_ferm)
        bf["recipe"]["fermentables"].append(bf_ferm)

        if the_type == "Sugar" or "Extract" in the_type:
            bf["recipe"]["data"]["otherFermentables"].append(bf_ferm)
        else:
            bf["recipe"]["data"]["mashFermentables"].append(bf_ferm)

    @staticmethod
    def add_yeast(bf, yeast):
        bf_yeast = copy.deepcopy(BFUtil.OBJ_YEAST)

        bf_yeast["amount"] = 1  # just use package/vial instead of billion cells
        bf_yeast["attenuation"] = yeast["byAttenuation"]
        bf_yeast["flocculation"] = yeast["byYeastFloc"]
        bf_yeast["form"] = yeast["byYeastForm"]
        bf_yeast["laboratory"] = get_value(yeast, "byYeastLab", "Unknown")
        bf_yeast["maxTemp"] = f_to_c(yeast["byMaxTemp"])
        bf_yeast["minTemp"] = f_to_c(yeast["byMinTemp"])
        bf_yeast["name"] = yeast["byName"]
        bf_yeast["productId"] = get_value(yeast, "byLabID", "Unknown")
        bf_yeast["type"] = yeast["byYeastType"]

        bf["batchYeasts"].append(bf_yeast)
        bf["recipe"]["yeasts"].append(bf_yeast)

    @staticmethod
    def add_extra(bf, extra):
        name = extra["beName"]
        if name in BFUtil.EXTRAS_MAP:
            bf_extra = copy.deepcopy(BFUtil.EXTRAS_MAP[name])
            if bf_extra["unit"] == "ml":
                bf_extra["amount"] = oz_to_ml(extra["beAmount"])
            elif bf_extra["unit"] == "g":
                bf_extra["amount"] = oz_to_g(extra["beAmount"])
            bf["batchMiscs"].append(bf_extra)
            bf["recipe"]["miscs"].append(bf_extra)
        else:
            print(f"  - Extra/addition not found: [{name}]")

    @staticmethod
    def add_mash_step(bf, step):
        bf_step = copy.deepcopy(BFUtil.OBJ_MASH_STEP)

        bf_step["displayStepTemp"] = step["bsStepTemp"]
        bf_step["name"] = step["bsName"]
        bf_step["rampTime"] = get_value(step, "bsRiseTime", 0)
        bf_step["stepTemp"] = f_to_c(step["bsStepTemp"])
        bf_step["stepTime"] = get_value(step, "bsTime", 0)
        bf_step["type"] = "Temperature"  # TODO Other types?

        bf["recipe"]["mash"]["steps"].append(bf_step)

    @staticmethod
    def populate_mash(bf, i_brew):
        if "batchSteps" in i_brew:
            for step in i_brew["batchSteps"]:
                BFUtil.add_mash_step(bf, step)
        else:
            bf["recipe"]["mash"] = copy.deepcopy(BFUtil.BF_DEFAULT_MASH)
            return

        num_steps = len(bf["recipe"]["mash"]["steps"])
        bf["mashStepsCount"] = num_steps
        has_mashout = any(step["name"] == "Mash Out" for step in bf["recipe"]["mash"]["steps"])

        mash_name = "Single Infusion"
        if "batchProfiles" in i_brew and i_brew["batchProfiles"]:
            mash_name = i_brew["batchProfiles"][0]["bpName"]
        elif has_mashout:
            if num_steps == 2:
                mash_name += ", Mash Out"
            else:
                mash_name = "Step Mash, Mash Out"
        elif num_steps > 1:
            mash_name = "Step Mash"

        bf["recipe"]["mash"]["name"] = mash_name


def main():
    """
    Application entry point
    """
    print("Convert iBrewMaster batch JSON to Brewfather batch JSON...")

    parser = argparse.ArgumentParser(description="iBrewMaster to Brewfather Converter")
    parser.add_argument("-f", "--file", nargs="+", required=True, type=str, help="Path to .json file(s) to convert")
    parser.add_argument("--brewer", type=str, required=True, help="Brewer name")
    parser.add_argument("-n", "--start-batch-num", default=1, type=int, help="Starting batch number")
    parser.add_argument("--metric", action="store_true", default=False,
                        help="Use SI/metric units instead of US customary/imperial")

    args = parser.parse_args()
    global USE_METRIC
    USE_METRIC = args.metric

    util = BFUtil()
    util.batch_number = args.start_batch_num
    util.brewer = args.brewer
    batches = []
    for filename in args.file:
        with open(filename) as file:
            to_convert = json.load(file)
            if "batches" in to_convert:
                for i_brew in to_convert["batches"]:
                    batches.append(util.convert(i_brew))
            elif isinstance(to_convert, list):
                batches.append(util.convert(to_convert))

    directory = "converted"
    os.makedirs(directory, exist_ok=True)
    for batch in batches:
        with open(f"{directory}/Batch{batch['batchNo']:03d}.json", "w") as file:
            json.dump(batch, file, indent=2)


if __name__ == '__main__':
    main()
