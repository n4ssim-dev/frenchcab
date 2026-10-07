import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ReservationsTable } from './reservations-table';

describe('ReservationsTable', () => {
  let component: ReservationsTable;
  let fixture: ComponentFixture<ReservationsTable>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ReservationsTable],
    }).compileComponents();

    fixture = TestBed.createComponent(ReservationsTable);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
