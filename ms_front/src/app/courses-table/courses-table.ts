import { DecimalPipe, DatePipe } from '@angular/common';
import { Component, computed, effect, inject, input, linkedSignal, signal } from '@angular/core';
import { Course, CoursesService } from '../courses.service';
import { Pagination } from '../pagination/pagination';

@Component({
  selector: 'app-courses-table',
  imports: [DatePipe, DecimalPipe, Pagination],
  templateUrl: './courses-table.html',
  styleUrl: './courses-table.scss',
})
export class CoursesTable {
  private service = inject(CoursesService);

  /** Date AAAA-MM-JJ initiale : si elle est absente, on affiche toutes les courses. */
  date = input<string | null>(null);
  /** Filtre modifiable depuis la barre d'outils. */
  filtreDate = linkedSignal(() => this.date());

  taille = signal(25);
  // repasse à la page 0 dès que la date ou la taille de page change
  page = linkedSignal(() => {
    this.filtreDate();
    this.taille();
    return 0;
  });

  courses = signal<Course[]>([]);
  total = signal(0);
  chargement = signal(false);
  erreur = signal<string | null>(null);
  nbPages = computed(() => Math.max(1, Math.ceil(this.total() / this.taille())));

  constructor() {
    effect((onCleanup) => {
      const date = this.filtreDate();
      const taille = this.taille();
      const page = this.page();
      this.chargement.set(true);
      this.erreur.set(null);

      const abonnement = this.service.getCourses(taille, page * taille, date).subscribe({
        next: (reponse) => {
          this.courses.set(reponse.courses);
          this.total.set(reponse.total);
          this.chargement.set(false);
        },
        error: (err) => {
          this.courses.set([]);
          this.total.set(0);
          this.erreur.set(err?.error?.message ?? 'Impossible de contacter le gateway.');
          this.chargement.set(false);
        },
      });
      // annule la requête précédente si un filtre change
      onCleanup(() => abonnement.unsubscribe());
    });
  }

  choisirDate(valeur: string) {
    this.filtreDate.set(valeur || null);
  }

  /** Durée de la course en minutes, calculée à partir des horaires. */
  duree(c: Course): number {
    return Math.round((new Date(c.arrivee).getTime() - new Date(c.depart).getTime()) / 60000);
  }
}
