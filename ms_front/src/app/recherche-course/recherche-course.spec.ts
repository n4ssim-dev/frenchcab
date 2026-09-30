import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RechercheCourse } from './recherche-course';

describe('RechercheCourse', () => {
  let component: RechercheCourse;
  let fixture: ComponentFixture<RechercheCourse>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RechercheCourse],
    }).compileComponents();

    fixture = TestBed.createComponent(RechercheCourse);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
