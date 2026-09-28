const express = require("express");
const router = express.Router();
const metierController = require("../controllers/metier_controllers");

router.get("/courses", metierController.getCourses);

module.exports = router;