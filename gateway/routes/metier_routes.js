const express = require("express");
const router = express.Router();
const metierController = require("../controllers/metier_controllers");

router.get("/courses", metierController.getCourses);
router.get("/courses/:id", metierController.getCourse);

module.exports = router;