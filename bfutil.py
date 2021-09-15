import argparse
import copy
import json
import os
from datetime import date, datetime, time

SIX_HOURS_MILLIS = 6 * 60 * 60 * 1000

BF_BATCH_FERM = "batchFermentables"
BF_BATCH_HOPS = "batchHops"
BF_BATCH_MISC = "batchMiscs"
BF_BATCH_YEAST = "batchYeasts"

BF_RECIPE_FERM = "fermentables"
BF_RECIPE_HOPS = "hops"
BF_RECIPE_MISC = "miscs"
BF_RECIPE_YEAST = "yeasts"

BF_RECIPE_MASH_FERM = "mashFermentables"
BF_RECIPE_OTHER_FERM = "otherFermentables"


def load_object(filename):
    with open("templates/" + filename) as f:
        obj = json.load(f)
        # print(json.dumps(obj, indent=2))
        return obj


def to_epoch_millis(date_str):
    the_date = date.fromisoformat(date_str)
    brew_date = datetime.combine(the_date, time(12))  # noon local
    return int(brew_date.timestamp() * 1000)


def gal_to_l(gallons):
    return gallons * 3.78541


def get_by_entry(array, key, value, key_to_get):
    for obj in array:
        if key in obj and obj[key] == value:
            if key_to_get in obj:
                return obj[key_to_get]
    return None


def f_to_c(temp):
    return (temp - 32) / 1.8


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


def get_value(i_brew, key, default=0):
    if key in i_brew:
        return i_brew[key]
    else:
        print(f"  - Missing key {key}, returning {default}")
        return default


class BFUtil:
    OBJ_YEAST = load_object("yeast.json")
    OBJ_FERM = load_object("fermentable.json")
    OBJ_HOPS = load_object("hops.json")
    OBJ_CACL2 = load_object("cacl2.json")
    OBJ_CASO4 = load_object("gypsum.json")
    OBJ_ACID = load_object("lactic_acid.json")
    OBJ_SUPERMOSS = load_object("supermoss.json")
    OBJ_WHIRLFLOC = load_object("whirlfloc.json")
    OBJ_NUTRIENT = load_object("yeast_nutrient.json")
    BF_TEMPLATE = load_object("brewfather-batch.json")

    def __init(self):
        self.batch_number = 1

    def convert(self, i_brew):
        # Copy the Brewfather template
        bf = copy.deepcopy(BFUtil.BF_TEMPLATE)

        bf["batchNo"] = self.batch_number
        print(f"Processing {i_brew['batchName']} as Batch #{self.batch_number}")

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

        # Set stats
        ibu = get_value(i_brew, "batchEstIBU")
        og = get_actual_og(i_brew)
        bf["estimatedColor"] = i_brew["batchColor"]
        bf["estimatedFg"] = i_brew["batchEstFG"]
        bf["estimatedIbu"] = ibu
        bf["estimatedOg"] = i_brew["batchEstOG"]
        bf["measuredAbv"] = get_actual_abv(i_brew)
        bf["measuredFg"] = get_actual_fg(i_brew)
        bf["measuredOg"] = get_actual_og(i_brew)

        # Recipe
        recipe = bf["recipe"]
        recipe["abv"] = i_brew["batchEstABV"]
        recipe["batchSize"] = gal_to_l(i_brew["batchSize"])
        recipe["boilSize"] = gal_to_l(i_brew["batchBoilSize"])
        recipe["boilTime"] = get_value(i_brew, "batchBoilTime")
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

        if "batchFerms" in i_brew:
            temp = get_by_entry(i_brew["batchFerms"], "bfName", "Primary", "bfTemp")
            if temp is not None:
                recipe["primaryTemp"] = f_to_c(temp)

        mash_temp, mash_time = get_mash_step(i_brew)
        if mash_temp is not None:
            mash = recipe["mash"]["steps"][0]
            mash["displayStepTemp"] = mash_temp
            mash["stepTemp"] = f_to_c(mash_temp)
            mash["stepTime"] = mash_time

        self.batch_number += 1
        return bf


def main():
    """
    Application entry point
    """
    print("Convert iBrewMaster batch JSON to Brewfather batch JSON...")

    parser = argparse.ArgumentParser(description="iBrewMaster to Brewfather Converter")
    parser.add_argument("-f", "--file", nargs="+", required=True, type=str, help="Path to .json file(s) to convert")
    parser.add_argument("-n", "--start-batch-num", required=True, type=int, help="Batch number")
    args = parser.parse_args()

    util = BFUtil()
    util.batch_number = args.start_batch_num
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
        with open(f"{directory}/Batch{batch['batchNo']}.json", "w") as file:
            json.dump(batch, file, indent=2)

    # print(json.dumps(batch))


if __name__ == '__main__':
    main()
