const reservationModel = require("../models/reservation_models.js");

function ajouterReservation(req,res){
    const reservation = req.body;

    reservationModel.createReservation(reservation,function(err){
        if(err) return res.status(500).json({message:"Erreur"});
        res.status(201).json({message:"Réservation ajoutée"});
    });
}


function listerReservations(req,res){
    reservationModel.getReservations((err,reservations)=>{
        if(err){
            return res.status(500).json({message:"Erreur"});
        }

        res.status(200).json(reservations);
    });
}

module.exports = {ajouterReservation,listerReservations};
