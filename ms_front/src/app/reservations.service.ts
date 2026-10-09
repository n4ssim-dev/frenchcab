import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../environments/environment';

// Adresse du gateway (selon l'environnement de build) et mot de passe (GATEWAY_PASSWORD du .env du gateway).
const GATEWAY_URL = environment.gatewayUrl;
const GATEWAY_PASSWORD = '5';



export interface PageReservations {
  total: number;
  limit: number;
  offset: number;
  reservations: Reservation[];
}

interface ReponseGateway {
  success: boolean;
  message: string;
  reponse: PageReservations;
}

export interface DemandeReservation {

  pickup: string;
  uid_client: number;
  resa_PU_locationID: number;
  resa_DO_locationID: number;
  resa_date: string;
  resa_heure: string;
  estimation_duree_course: number;
}

export interface ResultatReservation {
  uid_reservation: number;
  resa_PU_locationID: number;
  resa_DO_locationID: number;
  resa_date: string;
  resa_heure: string;
  estimation_duree_course: number;
  date_heure_reservation: string;
  statut_resa: number;
  uid_client: number;
  statut_nom: string;
}


export interface Reservation {
  uid_reservation: number;

  resa_PU_locationID: number;
  resa_DO_locationID: number;

  resa_date: string;
  resa_heure: string;

  estimation_duree_course: number | null;
  date_heure_reservation: string | null;

  statut_resa: number | null;
  uid_client: number | null;

  PU_locationID: number;
  zone_depart: string;

  DO_locationID: number;
  zone_arrivee: string;

  client_nom: string;
  client_email: string;

  // Statut
  statut_nom: string;
}


@Injectable({ providedIn: 'root' })
export class ReservationsService {
  private http = inject(HttpClient);

  getReservations(limit: number, offset: number, date: string | null): Observable<PageReservations> {
    let params = new HttpParams().set('limit', limit).set('offset', offset);

    if (date) {
      params = params.set('date', date); // format AAAA-MM-JJ
    }
    return this.http
      .get<ReponseGateway>(`${GATEWAY_URL}/reservations`, {
        params,
        headers: { 'x-api-password': GATEWAY_PASSWORD },
      })
      .pipe(map((r) => r.reponse));
  }

  reserver(demande: DemandeReservation): Observable<ResultatReservation> {
    return this.http
      .post<{ reponse: ResultatReservation }>(`${GATEWAY_URL}/reservation`, demande, {
        headers: { 'x-api-password': GATEWAY_PASSWORD },
      })
      .pipe(map((r) => r.reponse));
  }

}