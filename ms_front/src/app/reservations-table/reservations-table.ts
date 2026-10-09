import { DecimalPipe, DatePipe } from '@angular/common';
import { Component, computed, effect, inject, input, linkedSignal, signal } from '@angular/core';
import { Reservation, ReservationsService } from '../reservations.service';

@Component({
  selector: 'app-reservations-table',
  imports: [DatePipe, DecimalPipe],
  templateUrl: './reservations-table.html',
  styleUrl: './reservations-table.scss',
})
export class ReservationsTable {
  private service = inject(ReservationsService);

  /** Date AAAA-MM-JJ : si elle est absente, on affiche toutes les courses. */
  date = input<string | null>(null);

  readonly limit = 100;
  // repasse à la page 0 dès que la date change 
  page = linkedSignal(() => {
    this.date();
    return 0;
  });

  reservations = signal<Reservation[]>([]);
  total = signal(0);
  chargement = signal(false);
  erreur = signal<string | null>(null);
  nbPages = computed(() => Math.max(1, Math.ceil(this.total() / this.limit)));

  constructor() {
    effect((onCleanup) => {
      const date = this.date();
      const page = this.page();
      this.chargement.set(true);
      this.erreur.set(null);

      const abonnement = this.service.getReservations(this.limit, page * this.limit, date).subscribe({
        next: (reponse) => {
          this.reservations.set(reponse.reservations);
          this.total.set(reponse.total);
          this.chargement.set(false);
        },
        error: (err) => {
          this.reservations.set([]);
          this.total.set(0);
          this.erreur.set(err?.error?.message ?? 'Impossible de contacter le gateway.');
          this.chargement.set(false);
        },
      });
      // annule la requête précédente si la date ou la page change
      onCleanup(() => abonnement.unsubscribe());
    });
  }

  precedent() {
    this.page.update((p) => Math.max(0, p - 1));
  }

  suivant() {
    this.page.update((p) => Math.min(this.nbPages() - 1, p + 1));
  }
}

