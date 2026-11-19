
import json
import time
import math

EPSILON = 1e-9
SIZES = [3, 5, 13, 25]


# ==========================================
# 1. 라벨 정규화
# ==========================================

def normalize_label(label):
    value = str(label).strip().lower()

    if value in ("+", "cross"):
        return "Cross"

    if value == "x":
        return "X"

    return None


# ==========================================
# 2. MAC 연산
# ==========================================

def mac(pattern, filter_data):
    n = len(pattern)
    score = 0.0

    for i in range(n):
        for j in range(n):
            score += float(pattern[i][j]) * float(filter_data[i][j])

    return score


# ==========================================
# 3. 판정
# ==========================================

def classify(score_a, score_b):
    if abs(score_a - score_b) < EPSILON:
        return "UNDECIDED"

    if score_a > score_b:
        return "Cross"

    return "X"


# ==========================================
# 4. 입력 검증
# ==========================================

def input_matrix(name, n):
    print(f"\n{name} ({n}줄 입력, 공백 구분)")

    while True:
        matrix = []

        try:
            for i in range(n):
                row = list(map(float, input().split()))

                if len(row) != n:
                    raise ValueError

                if not all(math.isfinite(value) for value in row):
                    raise ValueError

                matrix.append(row)

            return matrix

        except ValueError:
            print(
                f"입력 형식 오류: "
                f"각 줄에 {n}개의 숫자를 공백으로 구분해 입력하세요."
            )
            print("처음부터 다시 입력해주세요.")
            matrix = []


# ==========================================
# 5. 성능 측정
# ==========================================

def benchmark(pattern, filter_data, repeat=10):
    start = time.perf_counter()

    for _ in range(repeat):
        mac(pattern, filter_data)

    end = time.perf_counter()

    return (end - start) * 1000 / repeat


def performance_analysis(filters=None):
    print("\n" + "=" * 55)
    print("[ 성능 분석 - 평균 10회 ]")
    print("=" * 55)

    print(f"{'크기':<15}{'평균 시간(ms)':<20}{'연산 횟수'}")
    print("-" * 55)

    for n in SIZES:
        if n == 3:
            pattern = [
                [0, 1, 0],
                [1, 1, 1],
                [0, 1, 0]
            ]
            filter_data = pattern

        elif filters and n in filters:
            filter_data = filters[n]["Cross"]
            pattern = filter_data

        else:
            pattern = [[1.0] * n for _ in range(n)]
            filter_data = pattern

        elapsed = benchmark(pattern, filter_data)

        print(
            f"{n}x{n:<12}"
            f"{elapsed:<20.6f}"
            f"{n * n}"
        )


# ==========================================
# 6. 사용자 입력 모드
# ==========================================

def user_mode():
    print("\n[1] 필터 입력")

    filter_a = input_matrix("필터 A", 3)
    filter_b = input_matrix("필터 B", 3)

    print("\n필터 A 저장 완료")
    print("필터 B 저장 완료")

    print("\n[2] 패턴 입력")

    pattern = input_matrix("패턴", 3)

    print("\n[3] MAC 결과")

    start = time.perf_counter()

    score_a = mac(pattern, filter_a)
    score_b = mac(pattern, filter_b)

    elapsed = (time.perf_counter() - start) * 1000

    result = classify(score_a, score_b)

    print(f"\nA 점수: {score_a}")
    print(f"B 점수: {score_b}")
    print(f"연산 시간: {elapsed:.6f} ms")

    if result == "UNDECIDED":
        print("판정: 판정 불가")
    else:
        print(f"판정: {result}")

    performance_analysis()


# ==========================================
# 7. JSON 데이터 분석 모드
# ==========================================

def json_mode():
    try:
        with open("data.json", "r", encoding="utf-8") as file:
            data = json.load(file)

    except FileNotFoundError:
        print("오류: data.json 파일을 찾을 수 없습니다.")
        return

    except json.JSONDecodeError:
        print("오류: JSON 파일 형식이 올바르지 않습니다.")
        return

    filters_data = data.get("filters", {})
    patterns_data = data.get("patterns", {})

    filters = {}
    failures = []
    total = 0
    passed = 0

    print("\n[1] 필터 로드")

    for n in (5, 13, 25):
        key = f"size_{n}"

        try:
            raw_filters = filters_data[key]

            normalized = {}

            for label, matrix in raw_filters.items():
                standard_label = normalize_label(label)

                if standard_label is None:
                    raise ValueError(f"알 수 없는 필터 라벨: {label}")

                if standard_label in normalized:
                    raise ValueError(f"중복 필터 라벨: {standard_label}")

                normalized[standard_label] = matrix

            if set(normalized) != {"Cross", "X"}:
                raise ValueError("Cross/X 필터가 모두 필요합니다.")

            for label, matrix in normalized.items():
                validate_matrix(matrix, n)

            filters[n] = normalized

            print(f"✓ {key} 필터 로드 완료 (Cross, X)")

        except (KeyError, TypeError, ValueError) as e:
            print(f"✗ {key} 필터 로드 실패: {e}")
            failures.append((key, str(e)))

    print("\n[2] 패턴 분석")

    for key, case in patterns_data.items():
        total += 1

        try:
            parts = key.split("_")

            if len(parts) < 3 or parts[0] != "size":
                raise ValueError("패턴 키 형식 오류")

            n = int(parts[1])

            if n not in (5, 13, 25):
                raise ValueError(f"지원하지 않는 크기: {n}")

            if n not in filters:
                raise ValueError(f"{n}x{n} 필터를 사용할 수 없습니다.")

            pattern = case["input"]
            expected = normalize_label(case["expected"])

            if expected is None:
                raise ValueError("expected 라벨 오류")

            validate_matrix(pattern, n)

            cross_score = mac(pattern, filters[n]["Cross"])
            x_score = mac(pattern, filters[n]["X"])

            result = classify(cross_score, x_score)

            status = "PASS" if result == expected else "FAIL"

            if status == "PASS":
                passed += 1
            else:
                reason = (
                    "동점 규칙"
                    if result == "UNDECIDED"
                    else f"예상값 {expected}, 실제값 {result}"
                )
                failures.append((key, reason))

            print(f"\n--- {key} ---")
            print(f"Cross 점수: {cross_score:.12f}")
            print(f"X 점수: {x_score:.12f}")
            print(f"판정: {result} | expected: {expected} | {status}")

        except (KeyError, TypeError, ValueError, IndexError) as e:
            failures.append((key, str(e)))
            print(f"\n--- {key} ---")
            print(f"FAIL: {e}")

    print("\n[3] 성능 분석")

    performance_analysis(filters)

    print("\n[시간 복잡도 분석]")
    print("MAC 연산은 N x N 행렬의 모든 원소를 한 번씩 계산합니다.")
    print("따라서 연산 횟수는 N²이며, 시간 복잡도는 O(N²)입니다.")

    print("\n[4] 결과 요약")
    print("=" * 45)

    print(f"전체 테스트: {total}개")
    print(f"통과: {passed}개")
    print(f"실패: {len(failures)}개")

    if failures:
        print("\n실패 케이스:")

        for key, reason in failures:
            print(f"- {key}: {reason}")

    else:
        print("\n모든 테스트 통과!")


# ==========================================
# 8. 행렬 검증
# ==========================================

def validate_matrix(matrix, n):
    if not isinstance(matrix, list) or len(matrix) != n:
        raise ValueError(f"행 개수 불일치: {n}개 필요")

    for row in matrix:
        if not isinstance(row, list) or len(row) != n:
            raise ValueError(f"열 개수 불일치: 각 행에 {n}개 필요")

        for value in row:
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("행렬에 숫자가 아닌 값이 있습니다.")

            if not float("-inf") < float(value) < float("inf"):
                raise ValueError("무한대 또는 NaN 값은 허용되지 않습니다.")


# ==========================================
# 9. 메인 프로그램
# ==========================================

def main():
    print("=" * 45)
    print("       Mini NPU Simulator")
    print("=" * 45)

    print("\n[모드 선택]")
    print("1. 사용자 입력 (3x3)")
    print("2. data.json 분석")

    while True:
        choice = input("\n선택: ").strip()

        if choice == "1":
            user_mode()
            break

        elif choice == "2":
            json_mode()
            break

        else:
            print("1 또는 2를 입력해주세요.")


if __name__ == "__main__":
    main()
