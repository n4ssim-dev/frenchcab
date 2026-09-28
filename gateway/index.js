const express = require("express"); 
const app = express();
const port = process.env.PORT;

const routesMetier = require("./routes/metier_routes");

app.use(express.json());

const cors = require("cors");
app.use(cors());

app.use("/metier", routesMetier);


app.listen(port, () => {
    console.log(`Gateway démarrée sur http://localhost:${port}`);
});