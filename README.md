## Introduction
This repo currently has a single utility to convert batches from *iBrewMaster 2* to *Brewfather*.

## Motivation

After over a decade of using *iBrewMaster* (and subsequently *iBrewMaster 2*) for brew tracking, I bought a new iPad and was dismayed to find that the app is not only no longer supported, but no longer available to even install!  

The sheer thought of losing my brewing history made me RDWHAHB (first world "problems"), but always nagged at me...  Not being able to go back and look at all the stupid things I had done as a newB, but more importantly, when and where I learned the things that I did from batch to batch, was completely unacceptable!

So, finally, I decided to do something about it.  

Fortunately, my OCD/anality allowed (forced?) me to back up my batches when I got my new iPad!  However, I could not do anything with them other than reading through the JSON to try and find nuggets I was looking for.  So, there they were, collecting dust from the Matrix, fading into fuzzy memory...  Every time I created a new recipe and brewed a new batch, I thought about all my brewing history, and whether there was something I was not considering...

So... Time to take action.  I decided to finally create something to convert my brewing history to the new application I was using (*Brewfather*!).

This repo is the result of that effort.  It converts batches exported from *iBrewMaster 2* into batches ready for import into *Brewfather* (including an embedded recipe).  It is not perfect, and likely does not handle every detail we Brewers care about, but it is "good enough" (at least for my purposes).

I invite you, my fellow Brewers, to try it out if you have a sordid brewing history sitting in *iBrewMaster 2* just waiting to move on to the next generation of brewing apps.

Keep calm, brew on!!!

## Requirements
This repo uses Python 3, because it was the language that I was playing with at the time.  There are no external dependencies, so you don't need to use a virtual environment or download any additional packages...

To convert from *iBrewMaster 2* to *Brewfather* batches, you will need your backups from *iBrewMaster 2* in JSON format.  Your backups can have any number of batches per file, and you can process all of your backup files in a single call.

## Application Usage
To see usage, run `python bfutil.py --help`.

To convert batches, run the following: `python bfutil.py --brewer "<name>" --file <files>`, where `"<name>"` is your name (or your brewery name), and `<files>` is the list of *iBrewMaster 2* backup JSON files you wish to convert.

This will create converted batches starting at Batch #1 in the `converted/` directory.  If you want to start from a different batch number, add the `--start-batch-num N` option, where `N` is the starting batch number.

By default, the application expects units in the *iBrewMaster 2* JSON backup files to be in US customary/imperial units (e.g. oz, gallons, etc.).  These are subsequently converted to SI/metric units by the application.  If your backups are already in SI/metric units, then pass the `--metric` option to the application.

To import the resulting JSON files into *Brewfather*, you will need to go to the **Recipes** section in *Brewfather*, and click the **Import** (![Import](assets/import.png)) button at the top right of the page.  When prompted, choose **Brewfather JSON** as the import format, and then **IMPORT AS BATCH** at the next prompt to import the file as a batch (as opposed to just a recipe).

## Feedback

Please tell me what you want to add to the existing functionality, or if you are a developer, please submit pull requests to update!

I welcome all requests for additional functionality, or things I completely screwed up!  The base functionality is based on my backup and current (very limited) *Brewfather* experience, so I am positive there are things I missed!

## Limitations
*Brewfather* JSON batch files are currently generated as one batch per file, which also means you need to import them one-by-one.  I experimented with generating all batches to a single file, and while *Brewfather* recognized the file and began the import, it did not actually generate any batches within the application, and gave no errors to try and diagnose the problem :(.

Equipment is currently assigned to my personal equipment.  If you want a different equipment setup (which you likely will), you can replace the contents of the `templates/equipment.json` with your equipment profile from a *Brewfather* export.

Beer styles are not configured during the conversion process (primarily because *iBrewMaster 2* used 2008 BJCP guidelines, whilst *Brewfather* uses 2015).  I recommend editing the batch recipe through *Brewfather* after import to set to the style you expect.

Because I live in the US, I have not tested the `--metric` option, other than making sure it does not convert most units from the backup files.  If you use this, please check that the resulting units are what you expect.  In particular, *Brewfather* uses grams almost everywhere except for malt/fermentable measurements, in which it uses kg.  Because *iBrewMaster 2* stored US/imperial weights in oz, I made the assumption that it would use grams instead of kg for mass/weight.  This assumption may be incorrect (please let me know if it is!).

Measurements for additions/extras (e.g. water agents, spices, flavorings, etc.) may be off, depending upon the units you used in *iBrewMaster 2*.  Unfortunately, the units are not included in the JSON, so I basically have to guess when converting.  I made a few basic assumptions:
 - Any mash additions are assumed to be in grams, regardless of measurement system used.  So, the amounts will not be converted (this includes any addition with "Mash" as the use for *Brewfather*)
 - Yeast Nutrient, Irish Moss, and Supermoss amounts are calculated in grams based on batch size, ignoring the amount in *iBrewMaster 2*
 - All other additions that are measured in either grams or ml in *Brewfather* are converted from oz or floz if not using the `--metric` option.  See the file `templates/extras_map.json` for details. 