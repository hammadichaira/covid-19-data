import os

import pandas as pd

from cowidev.utils import paths
from cowidev.testing import CountryTestBase


class Argentina(CountryTestBase):
    location: str = "Argentina"
    units: str = "tests performed"
    source_label: str = "Government of Argentina"
    source_url: str = "https://sisa.msal.gov.ar/datos/descargas/covid-19/files/Covid19Determinaciones.zip"
    source_url_ref: str = "https://datos.gob.ar/dataset/salud-covid-19-determinaciones-registradas-republica-argentina/archivo/salud_0de942d4-d106-4c74-b6b2-3654b0c53a3a"
    notes: str = pd.NA
    rename_columns: dict = {"fecha": "Date", "total": "Daily change in cumulative total", "positivos": "positive"}

    def read(self) -> pd.DataFrame:
        df = pd.read_csv(
            "https://sisa.msal.gov.ar/datos/descargas/covid-19/files/Covid19Determinaciones.zip",
            usecols=["fecha", "total", "positivos"],
        )
        return df

    def pipe_rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.rename(columns=self.rename_columns)

    def pipe_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        # Occasional errors where some lab inserts data before 2020
        df = df[df.Date >= "2020"]
        # Groupby
        df = df.groupby("Date", as_index=False).sum()
        # PR
        df["Positive rate"] = (
            df.positive.rolling(7).sum().div(df["Daily change in cumulative total"].rolling(7).sum()).round(3)
        )
        # Clean
        df = df[df["Daily change in cumulative total"] > 0].drop(columns=["positive"])
        return df

    def pipe_metadata(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.assign(
            **{
                "Country": self.location,
                "Units": self.units,
                "Notes": self.notes,
                "Source URL": self.source_url_ref,
                "Source label": self.source_label,
            }
        )

    def pipeline(self, df: pd.DataFrame) -> pd.DataFrame:
        return df.pipe(self.pipe_rename_columns).pipe(self.pipe_metrics).pipe(self.pipe_metadata)

    def export(self):
        df = self.read().pipe(self.pipeline)
        output_path = os.path.join(paths.SCRIPTS.OLD, "testing", "automated_sheets", f"{self.location}.csv")
        df.to_csv(output_path, index=False)


def main():
    Argentina().export()


if __name__ == "__main__":
    main()
