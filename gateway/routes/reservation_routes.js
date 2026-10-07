const express = require("express");
const router = express.Router();
const reservationController = require("../controllers/reservation_controllers.js");

router.post("/",reservationController.ajouterReservation);
router.get("/",reservationController.listerReservations);

module.exports = router;