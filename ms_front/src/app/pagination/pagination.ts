import { DecimalPipe } from '@angular/common';
import { Component, input, model } from '@angular/core';

/** Pagination partagée par les tableaux : page courante (base 0) + choix de la taille de page. */
@Component({
  selector: 'app-pagination',
  imports: [DecimalPipe],
  templateUrl: './pagination.html',
  styleUrl: './pagination.scss',
})
export class Pagination {
  page = model(0);
  taille = model(25);
  nbPages = input(1);
  desactive = input(false);

  readonly tailles = [10, 25, 50];

  precedent() {
    this.page.update((p) => Math.max(0, p - 1));
  }

  suivant() {
    this.page.update((p) => Math.min(this.nbPages() - 1, p + 1));
  }

  changerTaille(valeur: string) {
    this.taille.set(Number(valeur));
    this.page.set(0);
  }
}
