import { AfterViewChecked, Component, EventEmitter, OnDestroy, OnInit, Output, ViewChild } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { CdmStateService } from '../../../services/cdm-state.service';
import { BaseComponent } from '../../shared/base/base.component';
import { FakeDataStateService } from '../../../services/fake-data-state.service';
import { DbSettings } from '../../model/db-settings';
import { FakeDataParams } from '../../model/fake-data-params';
import { CdmSourceFormComponent } from './cdm-source-form/cdm-source-form.component';
import { CdmDestinationFormComponent } from './cdm-destination-form/cdm-destination-form.component';
import { CdmSettings } from '../../model/cdm-settings';
import { dictionaryDbSettingForCdmBuilder } from '../../scan-data.constants';

@Component({
  selector: 'app-cdm-form',
  templateUrl: './cdm-form.component.html',
  styleUrls: [
    './cdm-form.component.scss',
    '../../styles/scan-data-buttons.scss',
    '../../styles/scan-data-normalize.scss'
  ]
})
export class CdmFormComponent extends BaseComponent implements OnInit, AfterViewChecked, OnDestroy {

  sourceDbSettings: DbSettings;

  destinationDbSettings: DbSettings;

  sourceDataType: string;

  destinationDataType: string;

  fakeDataParams: FakeDataParams;

  isConvertButtonDisabled = true;

  @Output()
  convert = new EventEmitter<CdmSettings>();

  @ViewChild(CdmSourceFormComponent)
  sourceFormComponent: CdmSourceFormComponent;

  @ViewChild(CdmDestinationFormComponent)
  destinationFormComponent: CdmDestinationFormComponent;

  constructor(private formBuilder: FormBuilder,
              private cdmStateService: CdmStateService,
              private fakeDataStateService: FakeDataStateService) {
    super();
  }

  ngOnInit(): void {
    this.loadState();
  }

  ngAfterViewChecked(): void {
    // After checked child forms
    setTimeout(() => {
      this.isConvertButtonDisabled = this.sourceFormComponent.isNotValid || this.destinationFormComponent.isNotValid;
    });
  }

  ngOnDestroy() {
    super.ngOnDestroy();
    this.saveState();
  }

  onConvert() {
    const settings = this.createCdmBuilderSettings();
    this.convert.emit(settings);
  }

  private loadState() {
    const {sourceDbSettings, destinationDbSettings} = this.cdmStateService.state;
    const fakeDataParams = this.fakeDataStateService.state;

    this.sourceDataType = sourceDbSettings.dbType;
    this.destinationDataType = destinationDbSettings.dbType;
    this.sourceDbSettings = sourceDbSettings;
    this.destinationDbSettings = destinationDbSettings;
    this.fakeDataParams = fakeDataParams;
  }

  private saveState() {
    this.cdmStateService.state = {
      sourceDbSettings: {
        dbType: this.sourceFormComponent.dataType,
        ...this.sourceFormComponent.form.value
      },
      destinationDbSettings: {
        dbType: this.destinationFormComponent.dataType,
        ...this.destinationFormComponent.form.value
      }
    };
  }

  private createCdmBuilderSettings(): CdmSettings {
    const result = {
      ...this.sourceFormComponent.settings,
      ...this.destinationFormComponent.settings,
      ...dictionaryDbSettingForCdmBuilder
    };
    return result as CdmSettings;
  }
}

