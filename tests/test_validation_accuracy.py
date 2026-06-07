"""Validation accuracy testing framework for ORCA-LSP"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
from orca_lsp.parser import ORCAParser


@dataclass
class ValidationTestCase:
    """A test case for validation accuracy testing"""
    name: str
    content: str
    expect_errors: bool
    expect_warnings: bool
    category: str
    description: str = ""


class TestResult:
    """Result of a single test case"""

    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.tp_error = 0
        self.fp_error = 0
        self.tn_error = 0
        self.fn_error = 0
        self.tp_warning = 0
        self.fp_warning = 0
        self.tn_warning = 0
        self.fn_warning = 0
        self.errors_detected: List[str] = []
        self.warnings_detected: List[str] = []


class ValidationAccuracyTest:
    """Test framework for validation accuracy"""

    def __init__(self):
        self.parser = ORCAParser()
        self.test_results: List[TestResult] = []
        self.test_cases: List[ValidationTestCase] = []

    def add_test_case(self, case: ValidationTestCase):
        """Add a test case"""
        self.test_cases.append(case)

    def run_tests(self) -> dict:
        """Run all test cases and calculate accuracy metrics"""
        for case in self.test_cases:
            result = self.parser.parse(case.content)
            test_result = TestResult(case.name, case.category)

            test_result.errors_detected = [e["message"] for e in result.errors]
            test_result.warnings_detected = [w["message"] for w in result.warnings]

            has_errors = len(result.errors) > 0
            has_warnings = len(result.warnings) > 0

            if case.expect_errors:
                if has_errors:
                    test_result.tp_error = 1
                else:
                    test_result.fn_error = 1
            else:
                if has_errors:
                    test_result.fp_error = 1
                else:
                    test_result.tn_error = 1

            if case.expect_warnings:
                if has_warnings:
                    test_result.tp_warning = 1
                else:
                    test_result.fn_warning = 1
            else:
                if has_warnings:
                    test_result.fp_warning = 1
                else:
                    test_result.tn_warning = 1

            self.test_results.append(test_result)

        return self.calculate_metrics()

    def calculate_metrics(self) -> dict:
        """Calculate precision, recall, and F1 score"""
        tp = sum(r.tp_error + r.tp_warning for r in self.test_results)
        fp = sum(r.fp_error + r.fp_warning for r in self.test_results)
        fn = sum(r.fn_error + r.fn_warning for r in self.test_results)
        tn = sum(r.tn_error + r.tn_warning for r in self.test_results)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0.0

        return {
            "total_tests": len(self.test_results),
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": accuracy,
            "by_category": self._metrics_by_category(),
        }

    def _metrics_by_category(self) -> dict:
        """Calculate metrics by category"""
        categories = {}
        for result in self.test_results:
            if result.category not in categories:
                categories[result.category] = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
            categories[result.category]["tp"] += result.tp_error + result.tp_warning
            categories[result.category]["fp"] += result.fp_error + result.fp_warning
            categories[result.category]["tn"] += result.tn_error + result.tn_warning
            categories[result.category]["fn"] += result.fn_error + result.fn_warning

        metrics = {}
        for cat, counts in categories.items():
            total_positives = counts["tp"] + counts["fp"]
            total_actual = counts["tp"] + counts["fn"]
            if total_positives == 0 and total_actual == 0:
                p = 1.0
                r = 1.0
                f = 1.0
            elif total_positives == 0:
                p = 1.0
                r = counts["tp"] / total_actual if total_actual > 0 else 0.0
                f = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
            elif total_actual == 0:
                p = counts["tp"] / total_positives if total_positives > 0 else 0.0
                r = 1.0
                f = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
            else:
                p = counts["tp"] / total_positives if total_positives > 0 else 0.0
                r = counts["tp"] / total_actual if total_actual > 0 else 0.0
                f = 2 * (p * r) / (p + r) if (p + r) > 0 else 0.0
            metrics[cat] = {"precision": p, "recall": r, "f1": f, "tests": counts["tp"] + counts["tn"] + counts["fp"] + counts["fn"]}

        return metrics


def get_test_cases() -> List[ValidationTestCase]:
    """Get all validation test cases"""
    return [
        ValidationTestCase(
            name="scf_conflict_rhf_uhf",
            content="! RHF UHF def2-TZVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=True,
            expect_warnings=False,
            category="keywords",
            description="Mutually exclusive SCF types RHF and UHF",
        ),
        ValidationTestCase(
            name="scf_conflict_uhf_rohf",
            content="! UHF ROHF def2-TZVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=True,
            expect_warnings=False,
            category="keywords",
            description="Mutually exclusive SCF types UHF and ROHF",
        ),
        ValidationTestCase(
            name="scf_conflict_rhf_rohf",
            content="! RHF ROHF def2-TZVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=True,
            expect_warnings=False,
            category="keywords",
            description="Mutually exclusive SCF types RHF and ROHF",
        ),
        ValidationTestCase(
            name="scf_single_valid",
            content="! RHF def2-TZVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=False,
            expect_warnings=False,
            category="keywords",
            description="Single valid SCF type",
        ),
        ValidationTestCase(
            name="dft_mp2_warning",
            content="! B3LYP MP2 def2-TZVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=False,
            expect_warnings=True,
            category="methods",
            description="DFT combined with MP2 should warn",
        ),
        ValidationTestCase(
            name="hf_mp2_warning",
            content="! HF MP2 def2-TZVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=False,
            expect_warnings=True,
            category="methods",
            description="HF combined with MP2 should warn",
        ),
        ValidationTestCase(
            name="pbe_mp2_warning",
            content="! PBE MP2 def2-TZVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=False,
            expect_warnings=True,
            category="methods",
            description="PBE combined with MP2 should warn",
        ),
        ValidationTestCase(
            name="mp2_only_valid",
            content="! MP2 def2-TZVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=False,
            expect_warnings=False,
            category="methods",
            description="MP2 alone is valid",
        ),
        ValidationTestCase(
            name="dft_only_valid",
            content="! B3LYP def2-TZVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=False,
            expect_warnings=False,
            category="methods",
            description="DFT alone is valid",
        ),
        ValidationTestCase(
            name="ri_mp2_warning",
            content="! B3LYP RI-MP2 def2-TZVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=False,
            expect_warnings=True,
            category="methods",
            description="DFT combined with RI-MP2 should warn",
        ),
        ValidationTestCase(
            name="spin_multiplicity_zero",
            content="! RHF def2-TZVP\n%maxcore 2000\n* xyz 0 0\nH 0 0 0\n*",
            expect_errors=True,
            expect_warnings=False,
            category="chemistry",
            description="Invalid multiplicity (must be >=1)",
        ),
        ValidationTestCase(
            name="spin_valid_doublet",
            content="! RHF def2-TZVP\n%maxcore 2000\n* xyz 0 2\nH 0 0 0\n*",
            expect_errors=False,
            expect_warnings=False,
            category="chemistry",
            description="Valid doublet (single electron)",
        ),
        ValidationTestCase(
            name="spin_valid_triplet",
            content="! RHF def2-TZVP\n%maxcore 2000\n* xyz 0 3\nO 0 0 0\n*",
            expect_errors=False,
            expect_warnings=False,
            category="chemistry",
            description="Valid triplet for O atom",
        ),
        ValidationTestCase(
            name="basis_halogen_no_diffuse",
            content="! RHF def2-TZVP\n%maxcore 2000\n* xyz 0 1\nF 0 0 0\nCl 1 0 0\n*",
            expect_errors=False,
            expect_warnings=True,
            category="chemistry",
            description="Heavy halogens without diffuse functions",
        ),
        ValidationTestCase(
            name="basis_valid_def2svpd",
            content="! RHF def2-SVPD\n%maxcore 2000\n* xyz 0 1\nF 0 0 0\n*",
            expect_errors=False,
            expect_warnings=False,
            category="chemistry",
            description="def2-SVPD has diffuse functions",
        ),
        ValidationTestCase(
            name="standard_dft_valid",
            content="! B3LYP def2-TZVP\n%maxcore 2000\n* xyz 0 1\nC 0 0 0\nH 1 0 0\nH 0 1 0\nH 0 0 1\n*",
            expect_errors=False,
            expect_warnings=False,
            category="valid",
            description="Standard valid DFT input",
        ),
        ValidationTestCase(
            name="standard_mp2_valid",
            content="! MP2 def2-TZVP\n%maxcore 2000\n%pal nprocs 4 end\n* xyz 0 1\nC 0 0 0\nH 1 0 0\n*",
            expect_errors=False,
            expect_warnings=False,
            category="valid",
            description="Standard valid MP2 input",
        ),
        ValidationTestCase(
            name="ccsd_valid",
            content="! CCSD def2-TZVP\n%maxcore 4000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=False,
            expect_warnings=False,
            category="valid",
            description="CCSD is a valid method",
        ),
        ValidationTestCase(
            name="ri_jcosx_valid",
            content="! RHF RIJCOSX def2-TZVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*",
            expect_errors=False,
            expect_warnings=False,
            category="valid",
            description="RIJCOSX is valid with RHF",
        ),
    ]


class TestValidationAccuracy:
    """Pytest-compatible test class"""

    def test_keyword_conflicts(self):
        """Test mutually exclusive keyword detection"""
        test = ValidationAccuracyTest()
        for case in get_test_cases():
            if case.category == "keywords":
                test.add_test_case(case)

        metrics = test.run_tests()
        assert metrics["f1"] >= 0.90, f"Keyword conflict F1: {metrics['f1']:.2f}"

    def test_method_combinations(self):
        """Test method combination detection"""
        test = ValidationAccuracyTest()
        for case in get_test_cases():
            if case.category == "methods":
                test.add_test_case(case)

        metrics = test.run_tests()
        assert metrics["f1"] >= 0.90, f"Method combination F1: {metrics['f1']:.2f}"

    def test_spin_charge(self):
        """Test spin/charge validation"""
        test = ValidationAccuracyTest()
        for case in get_test_cases():
            if case.category == "chemistry":
                test.add_test_case(case)

        metrics = test.run_tests()
        assert metrics["f1"] >= 0.90, f"Spin/charge F1: {metrics['f1']:.2f}"

    def test_valid_cases(self):
        """Test that valid cases don't produce errors"""
        test = ValidationAccuracyTest()
        for case in get_test_cases():
            if case.category == "valid":
                test.add_test_case(case)

        metrics = test.run_tests()
        assert metrics["accuracy"] >= 0.90, f"Valid cases accuracy: {metrics['accuracy']:.2f}"

    def test_overall_accuracy(self):
        """Test overall validation accuracy"""
        test = ValidationAccuracyTest()
        for case in get_test_cases():
            test.add_test_case(case)

        metrics = test.run_tests()
        assert metrics["f1"] >= 0.90, f"Overall F1: {metrics['f1']:.2f}"
        assert metrics["precision"] >= 0.85, f"Overall precision: {metrics['precision']:.2f}"
        assert metrics["recall"] >= 0.90, f"Overall recall: {metrics['recall']:.2f}"

    def test_metrics_output(self):
        """Test that metrics are properly calculated and output"""
        test = ValidationAccuracyTest()
        for case in get_test_cases():
            test.add_test_case(case)

        metrics = test.run_tests()

        assert metrics["total_tests"] == 19
        assert "by_category" in metrics
        assert "keywords" in metrics["by_category"]
        assert "methods" in metrics["by_category"]
        assert "chemistry" in metrics["by_category"]
        assert "valid" in metrics["by_category"]


if __name__ == "__main__":
    test = ValidationAccuracyTest()
    for case in get_test_cases():
        test.add_test_case(case)

    metrics = test.run_tests()
    print("Validation Accuracy Results:")
    print("=" * 50)
    print(f"Total tests: {metrics['total_tests']}")
    print(f"True Positives: {metrics['true_positives']}")
    print(f"False Positives: {metrics['false_positives']}")
    print(f"True Negatives: {metrics['true_negatives']}")
    print(f"False Negatives: {metrics['false_negatives']}")
    print("=" * 50)
    print(f"Precision: {metrics['precision']:.2%}")
    print(f"Recall: {metrics['recall']:.2%}")
    print(f"F1 Score: {metrics['f1']:.2%}")
    print(f"Accuracy: {metrics['accuracy']:.2%}")
    print("=" * 50)
    print("By Category:")
    for category, cat_metrics in metrics["by_category"].items():
        print(f"  {category}: precision={cat_metrics['precision']:.2%}, recall={cat_metrics['recall']:.2%}, f1={cat_metrics['f1']:.2%}")