import { Component, signal } from '@angular/core';
import { CoursesTable } from '../courses-table/courses-table';

@Component({
  selector: 'app-recherche-course',
  imports: [CoursesTable],
  templateUrl: './recherche-course.html',
  styleUrl: './recherche-course.scss',
})
export class RechercheCourse {
  /** Date choisie au format AAAA-MM-JJ (celui de <input type="date">). */
  date = signal<string | null>(null);

  choisir(valeur: string) {
    this.date.set(valeur || null);
  }
}