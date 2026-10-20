const express = require("express");
const router = express.Router();
const metierController = require("../controllers/metier_controllers");

router.get("/courses", metierController.getCourses);
router.get("/courses/:id", metierController.getCourse);
router.post("/predictions/duree", metierController.predireDuree);
router.get("/modele", metierController.getModele);

router.post("/reservation", metierController.reservation); 
router.get("/reservations", metierController.listeReservations); 

router.patch("/reservations/:uid_reservation/statut",metierController.updateReservation);


module.exports = router;