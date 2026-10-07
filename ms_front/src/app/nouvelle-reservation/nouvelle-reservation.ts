import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CoursesService } from '../courses.service';
import { ReservationsService } from '../reservations.service';

@Component({
  selector: 'app-nouvelle-reservation',
  imports: [FormsModule],
  templateUrl: './nouvelle-reservation.html',
  styleUrl: './nouvelle-reservation.scss',
})
export class NouvelleReservation {
  private service = inject(CoursesService);
  private serviceReservation = inject(ReservationsService);

  pickup = signal('2026-07-15T18:10');
  depart = signal<number | null>(162);
  arrivee = signal<number | null>(236);
  distance = signal<number | null>(3.2);

  resultat = signal<number | null>(null);
  erreur = signal<string | null>(null);
  chargement = signal(false);

  predire() {
    const depart = this.depart();
    const arrivee = this.arrivee();
    const distance = this.distance();

    if (!this.pickup() || depart === null || arrivee === null || distance === null) {
      this.erreur.set('Remplis tous les champs.');
      return;
    }

    this.chargement.set(true);
    this.erreur.set(null);
    this.resultat.set(null);

    this.service
      .predireDuree({
        pickup: this.pickup(),
        id_location_depart: depart,
        id_location_arrivee: arrivee,
        distance,
      })
      .subscribe({
        next: (r) => {
          this.resultat.set(r.duree_predite_min);
          this.chargement.set(false);
        },
        error: (e) => {
          const message = e.error?.message;
          this.erreur.set(
            typeof message === 'string' ? message : "Impossible d'obtenir la prédiction.",
          );
          this.chargement.set(false);
        },
      });
  }
  
 reserver() {
    const depart = this.depart();
    const arrivee = this.arrivee();
    const distance = this.distance();


    if (!this.pickup() || depart === null || arrivee === null || distance === null) {
      this.erreur.set('Remplis tous les champs.');
      return;
    }

    this.chargement.set(true);
    this.erreur.set(null);
    this.resultat.set(null);

    this.serviceReservation
      .reserver({
        pickup: this.pickup(),
        id_location_depart: depart,
        id_location_arrivee: arrivee,
        distance,
      })
      .subscribe({
        next: (r) => {
         this.resultat.set(r.duree_predite_min);
          this.chargement.set(false);
        },
        error: (e) => {
          const message = e.error?.message;
          this.erreur.set(
            typeof message === 'string' ? message : "Impossible d'obtenir la prédiction.",
          );
          this.chargement.set(false);
        },
      });
  }
}


