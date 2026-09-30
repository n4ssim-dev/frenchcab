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
  ouvert = true;

  liens = [
    { label: 'Accueil', chemin: '/accueil' },
    { label: 'Recherche de course', chemin: '/patients' },
    { label: 'Liste des courses', chemin: '/parametres' }
  ];

  basculer() {
    this.ouvert = !this.ouvert;
  }
}