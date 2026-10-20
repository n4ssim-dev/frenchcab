import { Component } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.html',
  styleUrl: './sidebar.scss'
})
export class Sidebar {
  // menu déroulant sur mobile
  ouvert = false;

  liens = [
    { label: 'Réserver', chemin: '/nouvelle-reservation' },
    { label: 'Estimer un trajet', chemin: '/prediction' },
    { label: 'Réservations', chemin: '/liste-reservations' },
    { label: 'Historique des courses', chemin: '/liste-courses' },
  ];

  basculer() {
    this.ouvert = !this.ouvert;
  }

  fermer() {
    this.ouvert = false;
  }
}
