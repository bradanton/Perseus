import { Component, Input } from '@angular/core';
import { FormGroup } from '@angular/forms';

@Component({
  selector: 'app-cdm-connect-form',
  templateUrl: './cdm-connect-form.component.html',
  styleUrls: [
    '../cdm-form.component.scss',
    '../../../styles/scan-data-form.scss',
    '../../../styles/scan-data-connect-form.scss'
  ]
})
export class CdmConnectFormComponent {

  @Input()
  prefix = '';

  @Input()
  form: FormGroup;

  id(name: string): string {
    return `${this.prefix}-${name}`;
  }

  resetForm(){
    this.form.reset();
  }
}
