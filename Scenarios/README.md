# Developer Guide

## Motivation

Plaintext slide show format that could actually be tracked in version control (with diffs, etc.)


## Building

- [Node.js](https://nodejs.org/en/)
- [backslide](https://github.com/sinedied/backslide/)

On a sufficiently advanced system, it should be possible, once node is installed, to run `npm install -g backslide` and that'll be it. On my lesser Windows system, I needed to first run `npm install -g --production windows-build-tools` to get all the prerequisites to build some of the supporting libraries for backslide.


## Using/Running

Once everything's set up, running `bs serve` in the scenario folder should pop up a browser to let you view the slideshow. It will auto update for changes to the underlying documents, so any editor that's aware of Markdown is a fine tool. I used [Brackets](http://brackets.io/) because I was also changing CSS, but use whatever you have positive opinions of. 

You can also run `bs export` to make standalone HTML files (although the default uses absolute file references so these files may not render correctly on other machines), and `bs pdf` to make standalone PDFs (which apparently breaks if there are spaces in your filepath due to incorrect quotations, so you might need to take their broken command and correctly quote it to get the expected result). I'd prefer not to store these exported formats in the repo, so that we have exactly one canonical version of each scenario.


## Editing

Standard [markdown](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet) works. The underlying system is [remark](https://github.com/gnab/remark), so if you want to do something fancy you can go read and look at examples.


## Starting a New Scenario

Copy the `template` folder and the markdown for the scenario (`scenarioX.md`) to the new place, rename and edit the markdown as necessary, and run like normal (`bs serve`). 

The `bs init` command builds the initial `template` folder and a starting file to use, but I made a few changes to the stylesheets that would be lost if you started from scratch again. 