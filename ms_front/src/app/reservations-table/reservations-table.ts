import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, computed, effect, inject, linkedSignal, signal } from '@angular/core';
import { Reservation, ReservationsService } from '../reservations.service';
import { Pagination } from '../pagination/pagination';

// mêmes codes que l'API (ms_api_metier/routes/reservations.py)
const ANNULEE = 3;
const CLASSES_STATUT: Record<number, string> = { 0: 'attente', 1: 'confirmee', 2: 'terminee', 3: 'annulee' };

@Component({
  selector: 'app-reservations-table',
  imports: [DatePipe, DecimalPipe, Pagination],
  templateUrl: './reservations-table.html',
  styleUrl: './reservations-table.scss',
})
export class ReservationsTable {
  private service = inject(ReservationsService);

  // le gateway ne transmet pas limit/offset : on charge la liste et on pagine côté client
  readonly limitApi = 100;

  readonly filtres = [
    { label: 'Toutes', statut: null },
    { label: 'En attente', statut: 0 },
    { label: 'Confirmées', statut: 1 },
    { label: 'Terminées', statut: 2 },
  ];

  filtre = signal<number | null>(null);
  taille = signal(10);
  page = linkedSignal(() => {
    this.filtre();
    this.taille();
    return 0;
  });

  // incrémenté pour recharger la liste après une modification
  private rafraichir = signal(0);

  reservations = signal<Reservation[]>([]);
  chargement = signal(false);
  erreur = signal<string | null>(null);

  // annulation en cours de confirmation / d'envoi
  aConfirmer = signal<number | null>(null);
  enCours = signal<number | null>(null);
  message = signal<{ type: 'succes' | 'erreur'; texte: string } | null>(null);

  filtrees = computed(() => {
    const filtre = this.filtre();
    return filtre === null
      ? this.reservations()
      : this.reservations().filter((r) => r.statut_resa === filtre);
  });
  nbPages = computed(() => Math.max(1, Math.ceil(this.filtrees().length / this.taille())));
  visibles = computed(() => {
    const debut = this.page() * this.taille();
    return this.filtrees().slice(debut, debut + this.taille());
  });

  constructor() {
    effect((onCleanup) => {
      this.rafraichir();
      this.chargement.set(true);
      this.erreur.set(null);

      const abonnement = this.service.getReservations(this.limitApi, 0, null).subscribe({
        next: (reponse) => {
          this.reservations.set(reponse.reservations);
          this.chargement.set(false);
        },
        error: (err) => {
          this.reservations.set([]);
          this.erreur.set(err?.error?.message ?? 'Impossible de contacter le gateway.');
          this.chargement.set(false);
        },
      });
      onCleanup(() => abonnement.unsubscribe());
    });
  }

  nombre(statut: number | null): number {
    return statut === null
      ? this.reservations().length
      : this.reservations().filter((r) => r.statut_resa === statut).length;
  }

  classeStatut(statut: number | null): string {
    return CLASSES_STATUT[statut ?? -1] ?? '';
  }

  annulable(r: Reservation): boolean {
    // l'API autorise l'annulation depuis "en attente" et "confirmée"
    return r.statut_resa === 0 || r.statut_resa === 1;
  }

  annuler(uid_reservation: number): void {
    this.enCours.set(uid_reservation);
    this.message.set(null);

    this.service.updateReservation(uid_reservation, String(ANNULEE)).subscribe({
      next: () => {
        this.enCours.set(null);
        this.aConfirmer.set(null);
        this.message.set({ type: 'succes', texte: 'La réservation a été annulée.' });
        this.rafraichir.update((n) => n + 1);
      },
      error: (e) => {
        this.enCours.set(null);
        this.aConfirmer.set(null);
        const message = e.error?.message;
        this.message.set({
          type: 'erreur',
          texte: typeof message === 'string' ? message : "Impossible d'annuler la réservation.",
        });
      },
    });
  }
}
