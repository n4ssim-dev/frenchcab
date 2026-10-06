const reservationModel = require("../models/reservation_model.js");

function ajouterReservation(req,res){
    const reservation = req.body;

    reservationModel.createReservation(reservation,function(err){
        if(err) return res.status(500).json({message:"Erreur"});
        res.status(201).json({message:"Réservation ajoutée"});
    });
}

module.exports = {ajouterReservation};