const db = require("../database/db");

function createReservation(reservation,callback){
    const sql = `INSERT INTO reservations
    (resa_PU_locationID,resa_DO_locationID,resa_date,resa_heure,estimation_duree_course,date_heure_reservation,statut_resa,uid_trajet,locationID,locationID_1,uid_client)
    VALUES (?,?,?,?,?,?,?,?,?,?,?)`;

    db.run(sql,[
        reservation.resa_PU_locationID,
        reservation.resa_DO_locationID,
        reservation.resa_date,
        reservation.resa_heure,
        reservation.estimation_duree_course,
        reservation.date_heure_reservation,
        reservation.statut_resa,
        reservation.uid_trajet,
        reservation.locationID,
        reservation.locationID_1,
        reservation.uid_client
    ],callback);
}

module.exports = {createReservation};