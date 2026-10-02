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
  { label: 'Recherche de course', chemin: '/recherche-course' },
  { label: 'Liste des courses', chemin: '/liste-courses' },
  { label: 'Prédiction de durée', chemin: '/prediction' }
];

  basculer() {
    this.ouvert = !this.ouvert;
  }
}