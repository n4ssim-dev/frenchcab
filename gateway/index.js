require('dotenv').config();

const express = require("express"); 
const app = express();
const port = process.env.PORT;

const routesMetier = require("./routes/metier_routes");
const verifierMotDePasse = require("./middlewares/auth");
//const reservationRoutes = require("./routes/reservation_routes");

app.use(express.json());

const cors = require("cors");
app.use(cors());

app.use(verifierMotDePasse);

app.use("/metier", routesMetier);

//app.use("/api/reservations",reservationRoutes);


app.listen(port, () => {
    console.log(`Gateway démarrée sur http://localhost:${port}`);
});