import { Router } from "express";
const apiv1 = Router();

// Routes
apiv1.get("/", (req, res) => {
  res.send({
    message: "Hello from the API",
  });
});

// Catch all for unknown routes
apiv1.get("/*", (req, res) => {
	res.status(404).set({err: `Unknown api route: ${req.url}`});
});

export default apiv1;