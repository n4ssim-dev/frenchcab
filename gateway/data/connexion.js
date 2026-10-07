const sqlite3 = require("sqlite3").verbose();

const db = new sqlite3.Database("./data/taxi_test.db",(err)=>{
    if(err){
        console.log("Erreur connexion");
    }else{
        console.log("Connecté à SQLite");
    }
});

module.exports = db;