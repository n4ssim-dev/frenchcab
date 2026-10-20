import { Routes } from '@angular/router';
import { Accueil } from './accueil/accueil';
import { ListeCourses } from './liste-courses/liste-courses';
import { Prediction } from './prediction/prediction';
import { ListeReservations } from './liste-reservations/liste-reservations';
import { NouvelleReservation } from './nouvelle-reservation/nouvelle-reservation';

export const routes: Routes = [
  { path: '', redirectTo: 'accueil', pathMatch: 'full' },
  { path: 'accueil', component: Accueil },
  // la recherche par date est maintenant un filtre de la liste des courses
  { path: 'recherche-course', redirectTo: 'liste-courses' },
  { path: 'liste-courses', component: ListeCourses },
  { path: 'prediction', component: Prediction },
  { path: 'liste-reservations', component: ListeReservations },
  { path: 'nouvelle-reservation', component: NouvelleReservation },
  { path: '**', redirectTo: 'accueil' },
];
