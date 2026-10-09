import { Component } from '@angular/core';
import { ReservationsTable } from '../reservations-table/reservations-table';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-liste-reservations',
  imports: [ReservationsTable,RouterLink],
  templateUrl: './liste-reservations.html',
  styleUrl: './liste-reservations.scss',
})
export class ListeReservations {}