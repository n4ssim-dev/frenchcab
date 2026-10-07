import { ComponentFixture, TestBed } from '@angular/core/testing';
import { NouvelleReservation } from './nouvelle-reservation';

describe('NouvelleReservation', () => {
  let component: NouvelleReservation;
  let fixture: ComponentFixture<NouvelleReservation>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [NouvelleReservation],
    }).compileComponents();

    fixture = TestBed.createComponent(NouvelleReservation);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
