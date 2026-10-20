import { Component, input, model } from '@angular/core';
import { ZONES_PAR_QUARTIER } from '../zones';

/** Liste déroulante des zones de taxi, regroupées par quartier. */
@Component({
  selector: 'app-zone-select',
  templateUrl: './zone-select.html',
})
export class ZoneSelect {
  valeur = model<number | null>(null);
  label = input('Zone');
  nom = input('zone');
  invalide = input(false);

  readonly groupes = ZONES_PAR_QUARTIER;

  choisir(valeur: string) {
    this.valeur.set(valeur ? Number(valeur) : null);
  }
}
