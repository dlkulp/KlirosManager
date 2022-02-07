# KlirosManager
Manage your PDF and MusicXML files. Save, sort, and search your music efficiently and quickly with a variety of tags to quickly locate the music you're looking for!

Kliros Manager aims to create a platform to manage sheet music - sorting them into collections, detecting duplicate uploads, autocompleting metadata, and allowing minor edits from the comfort of your browser. The platform will provide a public library of free scores in the public domain but also allow users to keep scores in a private collection. Finally, the platform will provide the ability for directors to assemble private binders of music which can be shared with external users for use during rehearsals or services. 

Read more: [About](about/README.md)

## Dev stuff

### Client

cd into the /client folder, run `npm run dev` to run the front-end locally. Run `npm run build` to compile the ui and copy it into the /server folder for consumption there.

### Server

cd into the /server folder, run `npm start` to run the server locally. Hit all the UI routes like normal but now any /api/v1/* routes can be resolved.

#### Prisma

If db changes are needed, run `npx prisma db pull` to get the newest models then run `npx prisma generate` to create the client library.
