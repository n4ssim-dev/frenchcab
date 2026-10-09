import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { ListeReservations } from './liste-reservations';

describe('ListeReservations', () => {
  let component: ListeReservations;
  let fixture: ComponentFixture<ListeReservations>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ListeReservations],
      providers: [provideRouter([])],
    }).compileComponents();

    fixture = TestBed.createComponent(ListeReservations);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
