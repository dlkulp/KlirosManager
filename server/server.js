const express = require("express");
const app = express();
const port = 3030;

app.use(express.static("dist"));

app.listen(port, _ => {
  console.log(`listening on port ${port}!`);
});