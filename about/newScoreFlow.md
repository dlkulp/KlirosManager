1. User uploads image
    * Create a perceptual hash of the imagerceptual hash against public and user owned scores
2. If not a duplicate
    * Run DB query to check pecate
    * Use neural network to figure out bounding box for top of music score
    * Use OCR and use bounding box from NN to only parse the top of the music where the info is 
    * Autocomplete metadata from OCR data and allow user to change as necessary
3. If duplicate
    * Return potentially duplicated scores and allow the user to verify 
      1. is this actually a duplicate
      2. if it is truly a duplicate, which score is more legible and less marked up/noisy/discolored/etc

[<- Back](README.md)
