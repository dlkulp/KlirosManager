import apiv1 from "./v1/api";
import express from "express";
import bodyParser from "body-parser";
import Passport from "passport";
import auth from "./v1/auth";
import path from 'path';
import {fileURLToPath} from 'url';
import session from "express-session";
import Connect from "connect-sqlite3";
import "dotenv/config";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// This is dumb, the type file seems to be wrong....
let SQLiteStore = (Connect as any)(session);

const app = express();

app.use(session({
	secret: process.env["SESSION_SECRET"] as string,
	resave: false,
	saveUninitialized: false,
	store: new SQLiteStore({ db: "sessions.db", dir: path.resolve(__dirname, "db")})
}));
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());
app.use(Passport.authenticate("session"));

// API V1 routes
app.use("/api/v1/", apiv1);

// Last API route for unknown routes
app.get("/api/*", (req: any, res: any) => {
	res.status(404).send({err: `Unknown api version: ${req.url}`});
});

app.use("/", auth);

// Use compiled UI
app.use(express.static("dist/client"));

// Handles any non-API requests
app.get("*", (req: any,res: any) =>{
	console.log(req.url);
	res.sendFile(path.join(__dirname+"/dist/client/index.html"));
});

const port = process.env.port || 3030;

app.listen(port, () => {
	console.log(`listening on port ${port}!`);
});

export default app;