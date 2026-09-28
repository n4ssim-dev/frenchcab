const metier_models = require("../models/metier_models");


async function getCourses(req, res) {
  try {
    const reponse = await metier_models.getCourses();
    console.log(reponse);

    res.status(200).json({
      success: true,
      message: "La demande a été envoyée à l'API métier",
      reponse: reponse.data,
    });
  } catch (error) {
    res.status(error.response?.status || 500).json({
      success: false,
      message:
        error.response?.data?.detail ||
        "Impossible de contacter l'API métier.",
    });
  }
};

module.exports = {
  getCourses
};