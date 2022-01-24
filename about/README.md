# Primary Problem

Many (orthodox) choir directors have pdf libraries of music

* Different versions of the same piece to keep up some variety
* Less common pieces from the menaion which might not be used often and cycle which tone they're in
* Music in different styles (byzantine, slavic, georgian, znamenny, etc)
	
Difficult to search pdfs at OS level

Easy to lose less common pieces

No good way to categorize music except for very aggressive folder usage

Cannot really organize music in multiple ways (find all georgian in tone 3 or find all exapostilaria for Nativity) 

## Additional Considerations

Many church people are less than enthused about the internet and large corporations owning their data

* Local storage isn't backed up
* Local storage doesn't allow mobile and additional device usage

## Minimum Viable Product

1. Import pdfs, midi files, lyrics text files, image files
2. Manually fill in metadata (title, composer, etc)
  * Use combo boxes
    * Composer
    * Style
    * Feast
    * Etc
  * Dropdown for tone and difficulty
    * Calendar selection for fixed liturgical dates
    * Slider(?) for weeks after Pentecost
3. Mark for review (check visual hash for potential duplicates)
4. Save to cloud
5. Search based on metadata
6. Download resources
7. Mobile and Desktop clients - requires auth
8. Import music with mobile camera
9. Allow scores to be grouped with related midi files, lyrics files, and parts (soprano, alto, tenor, bass) (which are just other imported scores)
10. Allow scores to be put into collections of similar items (all the Our Fathers)
11. Allow scores to be put into order collections (binders) for particular feast days or ranks of feasts (allow export of entire binder as single pdf)

[User flow](newScoreFlow.md)

## Next Steps

* Add OCR to prepopulate metadata fields
* Add MusicXML support for generation of midi and additional output types
  * And maybe to support an in browser editor
* Maybe support the sale and purchase of scores…?

[Potential Frameworks](potentialLibraries.md)
