const express = require("express");
const router = express.Router();
const reservationController = require("../controllers/reservation_controllers.js");

router.post("/",reservationController.ajouterReservation);

module.exports = router;