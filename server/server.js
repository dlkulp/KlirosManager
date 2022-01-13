const express = require("express");
const bodyParser = require("body-parser");
const path = require("path");

const app = express();

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// API routes
app.get("/api/test", function(_req, res) {
	res.send({test: "Hello World!"});
});

// Last API route for unknown routes
app.get("/api/*", function(req, res) {
	res.status(404).send({err: `Unknown endpoint: ${req.url}`});
});

// Use compiled UI
app.use(express.static("dist"));

// Handles any non-API requests
app.get("*", (_req,res) =>{
    console.log(res);
    res.sendFile(path.join(__dirname+"/dist/index.html"));
});

const port = process.env.port || 3030;

app.listen(port, _ => {
  console.log(`listening on port ${port}!`);
});