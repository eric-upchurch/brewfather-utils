## Intro/Motivation

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

To convert from *iBrewMaster 2* to *Brewfather* batches, you will need your backups from *iBrewmaster 2* in JSON format.  Your backups can have any number of batches per file, and you can process all of your backup files in a single call.  I attempted to place them all in a single file for *Brewfather* to import, but was unsuccessful, so you will need to import each batch individually, one at a time :(.  I suggest sampling your previous batches to make sure they are not infected whilst you do this.

## Application Usage
To see usage, run `python bfutil.py --help`.

To convert batches, run the following: `python bfutil.py --file <files>`, where `<files>` is the list of *iBrewmaster 2* backup JSON files you wish to convert.

This will create converted batches starting at batch #1 in the `converted/` directory.  If you want to start from a different batch number, add the `--start-batch-num N` option, where `N` is the starting batch number.

By default, the application expects units in the *iBrewmaster 2* JSON backup files to be in US customary/imperial units (e.g. oz, gallons, etc.).  These are subsequently converted to SI/metric units by the application.  If your backups are already in SI/metric units, then pass the `--metric` option to the application.
## Feedback

Please tell me what you want to add to the existing functionality, or if you are a developer, please submit pull requests to update!

I welcome all requests for additional functionality, or things I completely screwed up!  The base functionality is based on my backup and current (very limited) *Brewfather* experience, so I am positive there are things I missed!

## Limitations
Equipment is currently assigned to my personal equipment.  If you want a different equipment setup (which you likely will), you can replace the contents of the `templates/equipment.json` with your equipment profile from a Brewfather export.

Because I live in the US, I have not tested the `--metric` option, other than making sure it does not convert most units from the backup files.  If you use this, please check that the resulting units are what you expect.  In particular, *Brewfather* uses grams almost everywhere except for malt/fermentable measurements, in which it uses kg.  Because *iBrewmaster 2* stored US/imperial weights in oz, I made the assumption that it would use grams instead of kg for mass/weight.  This assumption may be incorrect (please let me know if it is!).