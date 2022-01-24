import apiv1 from "./v1/api";
import express from "express";
import bodyParser from "body-parser";
import path from "path";

const app = express();

app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// API V1 routes
app.use("/api/v1/", apiv1);

// Last API route for unknown routes
app.get("/api/*", (req: any, res: any) => {
	res.status(404).send({err: `Unknown api version: ${req.url}`});
});

// Use compiled UI
app.use(express.static("dist"));

// Handles any non-API requests
app.get("*", (req: any,res: any) =>{
	console.log(req.url);
	res.sendFile(path.join(__dirname+"/dist/index.html"));
});

const port = process.env.port || 3030;

app.listen(port, () => {
	console.log(`listening on port ${port}!`);
});
