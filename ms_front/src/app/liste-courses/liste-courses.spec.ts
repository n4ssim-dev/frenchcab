import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ListeCourses } from './liste-courses';

describe('ListeCourses', () => {
  let component: ListeCourses;
  let fixture: ComponentFixture<ListeCourses>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ListeCourses],
    }).compileComponents();

    fixture = TestBed.createComponent(ListeCourses);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
