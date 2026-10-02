import { Routes } from '@angular/router';
import { Accueil } from './accueil/accueil';
import { RechercheCourse } from './recherche-course/recherche-course';
import { ListeCourses } from './liste-courses/liste-courses';
import { Prediction } from './prediction/prediction';

export const routes: Routes = [
  { path: '', redirectTo: 'accueil', pathMatch: 'full' },
  { path: 'accueil', component: Accueil },
  { path: 'recherche-course', component: RechercheCourse },
  { path: 'liste-courses', component: ListeCourses },
  { path: 'prediction', component: Prediction },
];