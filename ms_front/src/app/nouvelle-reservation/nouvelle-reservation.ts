import { Component, computed, inject, input, linkedSignal, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CoursesService } from '../courses.service';
import { ReservationsService, ResultatReservation } from '../reservations.service';
import { ZoneSelect } from '../zone-select/zone-select';
import { nomZone } from '../zones';

/** Convertit un query param en nombre (null s'il est absent ou invalide). */
function enNombre(valeur: unknown): number | null {
  const n = Number(valeur);
  return valeur === undefined || valeur === null || valeur === '' || Number.isNaN(n) ? null : n;
}

/** Date locale au format de <input type="datetime-local"> (AAAA-MM-JJTHH:MM). */
function dateLocale(date: Date): string {
  const decale = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return decale.toISOString().slice(0, 16);
}

@Component({
  selector: 'app-nouvelle-reservation',
  imports: [FormsModule, RouterLink, ZoneSelect],
  templateUrl: './nouvelle-reservation.html',
  styleUrl: './nouvelle-reservation.scss',
})
export class NouvelleReservation {
  private service = inject(CoursesService);
  private serviceReservation = inject(ReservationsService);

  // pré-remplissage optionnel depuis la page d'estimation (query params)
  qDepart = input(null, { alias: 'depart', transform: enNombre });
  qArrivee = input(null, { alias: 'arrivee', transform: enNombre });
  qDuree = input(null, { alias: 'duree', transform: enNombre });

  depart = linkedSignal<number | null>(() => this.qDepart());
  arrivee = linkedSignal<number | null>(() => this.qArrivee());
  duree = linkedSignal<number | null>(() => this.qDuree());
  // départ par défaut : dans 30 minutes
  pickup = signal(dateLocale(new Date(Date.now() + 30 * 60000)));
  client = signal<number | null>(1);

  // estimation facultative de la durée
  distance = signal<number | null>(null);
  estimation = signal(false);
  erreurEstimation = signal<string | null>(null);

  chargement = signal(false);
  soumis = signal(false);
  erreur = signal<string | null>(null);
  confirmation = signal<ResultatReservation | null>(null);

  readonly maintenant = dateLocale(new Date());
  readonly nomZone = nomZone;

  valide = computed(
    () =>
      this.depart() !== null &&
      this.arrivee() !== null &&
      !!this.pickup() &&
      (this.client() ?? 0) > 0 &&
      (this.duree() ?? 0) > 0,
  );

  estimer() {
    const depart = this.depart();
    const arrivee = this.arrivee();
    const distance = this.distance();

    if (depart === null || arrivee === null || !this.pickup() || !(distance! > 0)) {
      this.erreurEstimation.set('Renseigne le trajet, la date et la distance pour estimer.');
      return;
    }

    this.estimation.set(true);
    this.erreurEstimation.set(null);

    this.service
      .predireDuree({ pickup: this.pickup(), id_location_depart: depart, id_location_arrivee: arrivee, distance: distance! })
      .subscribe({
        next: (r) => {
          this.duree.set(Math.ceil(r.duree_predite_min));
          this.estimation.set(false);
        },
        error: (e) => {
          const message = e.error?.message;
          this.erreurEstimation.set(
            typeof message === 'string'
              ? message
              : "Estimation indisponible : saisis la durée à la main.",
          );
          this.estimation.set(false);
        },
      });
  }

  reserver() {
    this.soumis.set(true);
    if (!this.valide()) {
      this.erreur.set('Remplis tous les champs obligatoires.');
      return;
    }

    this.chargement.set(true);
    this.erreur.set(null);

    // la valeur de datetime-local est déjà en heure locale : pas de conversion UTC
    const [resa_date, resa_heure] = this.pickup().split('T');

    this.serviceReservation
      .reserver({
        pickup: this.pickup(),
        uid_client: this.client()!,
        resa_PU_locationID: this.depart()!,
        resa_DO_locationID: this.arrivee()!,
        resa_date,
        resa_heure: resa_heure.slice(0, 5),
        estimation_duree_course: this.duree()!,
      })
      .subscribe({
        next: (r) => {
          this.confirmation.set(r);
          this.chargement.set(false);
        },
        error: (e) => {
          const message = e.error?.message;
          this.erreur.set(
            typeof message === 'string' ? message : 'Impossible de faire la réservation.',
          );
          this.chargement.set(false);
        },
      });
  }

  nouvelle() {
    this.confirmation.set(null);
    this.soumis.set(false);
    this.erreur.set(null);
  }
}
