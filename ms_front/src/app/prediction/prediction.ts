import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { CoursesService } from '../courses.service';
import { ZoneSelect } from '../zone-select/zone-select';
import { nomZone } from '../zones';

@Component({
  selector: 'app-prediction',
  imports: [FormsModule, RouterLink, DatePipe, DecimalPipe, ZoneSelect],
  templateUrl: './prediction.html',
  styleUrl: './prediction.scss',
})
export class Prediction {
  private service = inject(CoursesService);

  pickup = signal('2026-07-15T18:10');
  depart = signal<number | null>(162);
  arrivee = signal<number | null>(236);
  distance = signal<number | null>(3.2);

  resultat = signal<number | null>(null);
  erreur = signal<string | null>(null);
  chargement = signal(false);
  soumis = signal(false);

  valide = computed(
    () =>
      !!this.pickup() &&
      this.depart() !== null &&
      this.arrivee() !== null &&
      (this.distance() ?? 0) > 0,
  );

  /** Heure d'arrivée estimée, affichée sous la durée. */
  arriveeEstimee = computed(() => {
    const minutes = this.resultat();
    if (minutes === null || !this.pickup()) return null;
    return new Date(new Date(this.pickup()).getTime() + minutes * 60000);
  });

  /** Paramètres pour pré-remplir le formulaire de réservation. */
  paramsReservation = computed(() => ({
    depart: this.depart(),
    arrivee: this.arrivee(),
    duree: this.resultat() === null ? null : Math.ceil(this.resultat()!),
  }));

  readonly nomZone = nomZone;

  predire() {
    this.soumis.set(true);
    if (!this.valide()) {
      this.erreur.set('Remplis tous les champs.');
      return;
    }

    this.chargement.set(true);
    this.erreur.set(null);
    this.resultat.set(null);

    this.service
      .predireDuree({
        pickup: this.pickup(),
        id_location_depart: this.depart()!,
        id_location_arrivee: this.arrivee()!,
        distance: this.distance()!,
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
