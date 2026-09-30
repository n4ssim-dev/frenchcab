import { DecimalPipe, DatePipe } from '@angular/common';
import { Component, computed, effect, inject, input, linkedSignal, signal } from '@angular/core';
import { Course, CoursesService } from '../courses.service';

@Component({
  selector: 'app-courses-table',
  imports: [DatePipe, DecimalPipe],
  templateUrl: './courses-table.html',
  styleUrl: './courses-table.scss',
})
export class CoursesTable {
  private service = inject(CoursesService);

  /** Date AAAA-MM-JJ : si elle est absente, on affiche toutes les courses. */
  date = input<string | null>(null);

  readonly limit = 100;
  // repasse à la page 0 dès que la date change
  page = linkedSignal(() => {
    this.date();
    return 0;
  });

  courses = signal<Course[]>([]);
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

      const abonnement = this.service.getCourses(this.limit, page * this.limit, date).subscribe({
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