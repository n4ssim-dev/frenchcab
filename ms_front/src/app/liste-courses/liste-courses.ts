import { Component } from '@angular/core';
import { CoursesTable } from '../courses-table/courses-table';

@Component({
  selector: 'app-liste-courses',
  imports: [CoursesTable],
  templateUrl: './liste-courses.html',
  styleUrl: './liste-courses.scss',
})
export class ListeCourses {}