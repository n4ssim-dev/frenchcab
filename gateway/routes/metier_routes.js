const express = require("express");
const router = express.Router();
const metierController = require("../controllers/metier_controllers");

router.get("/courses", metierController.getCourses);
router.get("/courses/:id", metierController.getCourse);
router.post("/predictions/duree", metierController.predireDuree);

router.post("/reservation", metierController.reservation); 
router.get("/reservations", metierController.listeReservations); 



module.exports = router;